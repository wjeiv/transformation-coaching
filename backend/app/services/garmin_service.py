import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError

from app.core.security import decrypt_value, encrypt_value

logger = logging.getLogger(__name__)


class GarminService:
    """Service for interacting with Garmin Connect API."""

    @staticmethod
    def _create_client(email: str, password: str) -> Garmin:
        """Create and authenticate a Garmin Connect client."""
        client = Garmin(email, password)
        client.login()
        return client

    @staticmethod
    async def test_connection(encrypted_email: str, encrypted_password: str) -> Tuple[bool, str]:
        """Test Garmin Connect connectivity with stored credentials."""
        try:
            email = decrypt_value(encrypted_email)
            password = decrypt_value(encrypted_password)
            client = GarminService._create_client(email, password)
            display_name = client.get_full_name()
            return True, f"Successfully connected to Garmin Connect as {display_name}"
        except GarminConnectAuthenticationError:
            return False, (
                "Authentication failed. The Garmin Connect credentials are invalid. "
                "Please verify the email and password are correct and that the account exists."
            )
        except GarminConnectConnectionError:
            return False, (
                "Could not connect to Garmin Connect servers. "
                "This may be a temporary issue. Please try again in a few minutes."
            )
        except Exception as e:
            logger.error(f"Garmin connection test failed: {e}")
            return False, f"Unexpected error connecting to Garmin Connect: {str(e)}"

    @staticmethod
    async def get_workouts(
        encrypted_email: str, encrypted_password: str
    ) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Fetch all workouts from a Garmin Connect account."""
        try:
            email = decrypt_value(encrypted_email)
            password = decrypt_value(encrypted_password)
            client = GarminService._create_client(email, password)

            workouts = client.get_workouts()
            result = []
            for w in workouts:
                workout_type = "other"
                sport_type = w.get("sportType", {})
                if isinstance(sport_type, dict):
                    sport_key = sport_type.get("sportTypeKey", "").lower()
                else:
                    sport_key = str(sport_type).lower()

                if "running" in sport_key or "run" in sport_key:
                    workout_type = "running"
                elif "cycling" in sport_key or "bik" in sport_key:
                    workout_type = "cycling"
                elif "swim" in sport_key:
                    workout_type = "swimming"
                elif "strength" in sport_key or "cardio" in sport_key:
                    workout_type = "strength"

                result.append({
                    "garmin_workout_id": str(w.get("workoutId", "")),
                    "workout_name": w.get("workoutName", "Unnamed Workout"),
                    "workout_type": workout_type,
                    "description": w.get("description", ""),
                    "workout_data": json.dumps(w),
                })
            return True, "Workouts fetched successfully", result
        except GarminConnectAuthenticationError:
            return False, "Authentication failed. Please re-enter your Garmin credentials.", []
        except GarminConnectConnectionError:
            return False, "Could not connect to Garmin Connect. Please try again later.", []
        except Exception as e:
            logger.error(f"Failed to fetch workouts: {e}")
            return False, f"Error fetching workouts: {str(e)}", []

    @staticmethod
    async def get_workout_details(
        encrypted_email: str, encrypted_password: str, workout_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Fetch detailed workout data from Garmin Connect."""
        try:
            email = decrypt_value(encrypted_email)
            password = decrypt_value(encrypted_password)
            client = GarminService._create_client(email, password)

            workout = client.get_workout_by_id(workout_id)
            return True, "Workout details fetched", workout
        except Exception as e:
            logger.error(f"Failed to fetch workout {workout_id}: {e}")
            return False, f"Error fetching workout details: {str(e)}", None

    @staticmethod
    async def import_workout(
        encrypted_email: str,
        encrypted_password: str,
        workout_data: Dict[str, Any],
    ) -> Tuple[bool, str, Optional[str]]:
        """Import a workout into an athlete's Garmin Connect account.

        This creates a new workout in the athlete's account based on the
        workout data exported from the coach's account.
        """
        try:
            email = decrypt_value(encrypted_email)
            password = decrypt_value(encrypted_password)
            client = GarminService._create_client(email, password)

            # Remove the original workoutId so Garmin creates a new one
            import_data = dict(workout_data)
            import_data.pop("workoutId", None)
            import_data.pop("ownerId", None)
            import_data.pop("createdDate", None)
            import_data.pop("updatedDate", None)

            result = client.save_workout(import_data)

            new_id = None
            if isinstance(result, dict):
                new_id = str(result.get("workoutId", ""))

            return True, "Workout imported successfully to Garmin Connect", new_id
        except GarminConnectAuthenticationError:
            return False, (
                "Authentication failed for athlete's Garmin account. "
                "The athlete needs to re-enter their Garmin credentials."
            ), None
        except GarminConnectConnectionError:
            return False, (
                "Could not connect to Garmin Connect. "
                "Please try again in a few minutes."
            ), None
        except Exception as e:
            logger.error(f"Failed to import workout: {e}")
            return False, f"Error importing workout: {str(e)}", None

    @staticmethod
    async def check_athlete_connection(
        encrypted_email: str, encrypted_password: str
    ) -> Dict[str, Any]:
        """Check if an athlete's Garmin Connect account is accessible.

        Returns detailed status with human-readable messages.
        """
        recommendations = []
        try:
            email = decrypt_value(encrypted_email)
            password = decrypt_value(encrypted_password)
            client = GarminService._create_client(email, password)
            display_name = client.get_full_name()

            return {
                "is_connected": True,
                "message": f"Connected to Garmin Connect as {display_name}. Ready for workout sync.",
                "recommendations": [],
            }
        except GarminConnectAuthenticationError:
            recommendations = [
                "Verify the Garmin Connect email address is correct",
                "Verify the Garmin Connect password is correct",
                "Check if the Garmin account has been locked due to too many failed attempts",
                "Try logging into connect.garmin.com directly to verify credentials",
            ]
            return {
                "is_connected": False,
                "message": "Cannot authenticate with Garmin Connect. The stored credentials are invalid.",
                "recommendations": recommendations,
            }
        except GarminConnectConnectionError:
            recommendations = [
                "Check if Garmin Connect is experiencing an outage at status.garmin.com",
                "Try again in a few minutes",
                "Verify your internet connection is stable",
            ]
            return {
                "is_connected": False,
                "message": "Cannot reach Garmin Connect servers.",
                "recommendations": recommendations,
            }
        except Exception as e:
            recommendations = [
                "Try disconnecting and reconnecting the Garmin account",
                "Contact support if the issue persists",
            ]
            return {
                "is_connected": False,
                "message": f"Unexpected error: {str(e)}",
                "recommendations": recommendations,
            }
