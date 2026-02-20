# Garmin Workout Import Debug Analysis

## Issue Summary
An athlete's imported workouts are not showing up in the Garmin Connect workout list, indicating the import process is not working properly.

## System Architecture

### 1. Database Models
- **User**: Stores athlete/coach information with Garmin credentials relationship
- **GarminCredentials**: Encrypted Garmin email/password, connection status, last sync
- **Workout**: Coach's workouts fetched from Garmin (garmin_workout_id, workout_data JSON)
- **SharedWorkout**: Links workouts to athletes with import status (pending/imported/failed)

### 2. Import Process Flow
1. Coach shares workout → Creates `SharedWorkout` record with status "pending"
2. Athlete triggers import → Calls `/athlete/workouts/import` endpoint
3. System validates Garmin credentials → Calls `GarminService.import_workout()`
4. Garmin API creates new workout → Returns new workout ID
5. Updates `SharedWorkout` status to "imported" with `garmin_import_id`

### 3. Key Files
- `backend/app/services/garmin_service.py` - Core Garmin Connect integration
- `backend/app/api/athlete.py` - Import endpoint logic
- `backend/app/models/user.py` - Database models

## Potential Issues & Debugging Steps

### Issue 1: Authentication Problems
**Symptoms**: Connection failures, invalid credentials
**Debug**: Check `GarminCredentials.is_connected` and `connection_error` fields
**Solution**: Re-authenticate athlete's Garmin account

### Issue 2: Workout Data Corruption
**Symptoms**: JSON decode errors, malformed workout data
**Debug**: Verify `workout.workout_data` contains valid JSON
**Solution**: Coach needs to re-share the workout

### Issue 3: Garmin API Changes
**Symptoms**: `client.save_workout()` fails, API errors
**Debug**: Check garminconnect library version, test with real credentials
**Solution**: Update garminconnect library or adapt to API changes

### Issue 4: Missing Database Commits
**Symptoms**: Import appears successful but status not updated
**Debug**: Check if `await db.flush()` is called after status updates
**Solution**: Ensure proper database transaction handling

### Issue 5: Workout ID Conflicts
**Symptoms**: Workout not visible due to ID conflicts
**Debug**: Check if `workoutId` is properly removed before import
**Solution**: Verify `import_data.pop("workoutId", None)` in import_workout()

## Recommended Debugging Actions

### 1. Check Database State
```sql
-- Find stuck workouts
SELECT sw.id, sw.status, sw.shared_at, sw.import_error, sw.garmin_import_id,
       w.workout_name, u_athlete.full_name
FROM shared_workouts sw
JOIN workouts w ON sw.workout_id = w.id
JOIN users u_athlete ON sw.athlete_id = u_athlete.id
WHERE sw.status IN ('pending', 'failed')
ORDER BY sw.shared_at DESC;
```

### 2. Test Garmin Connection
```python
# Test athlete's Garmin credentials
success, message = await GarminService.test_connection(
    encrypted_email, encrypted_password
)
```

### 3. Verify Workout Data
```python
# Check workout data integrity
workout_data = json.loads(shared.workout.workout_data)
print(f"Workout keys: {list(workout_data.keys())}")
```

### 4. Manual Import Test
```python
# Test import process manually
success, message, garmin_id = await GarminService.import_workout(
    encrypted_email, encrypted_password, workout_data
)
```

## Common Fixes

1. **Reconnect Garmin Account**: Athlete needs to re-enter credentials
2. **Clear Pending Workouts**: Remove stuck "pending" workouts older than 24h
3. **Update Library**: Ensure garminconnect==0.2.19 is installed
4. **Check Workout Format**: Verify workout data matches Garmin's expected schema

## Next Steps
1. Run the debug script to identify the specific failure point
2. Check application logs for detailed error messages
3. Test with a fresh workout import to isolate the issue
4. Verify the athlete's Garmin account has proper permissions
