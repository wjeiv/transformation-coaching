import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const API_URL = process.env.REACT_APP_API_URL || "/api/v1";

// Mobile detection
const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

// Mobile detection
const isMobile = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
};

const api = axios.create({
  baseURL: API_URL,
  headers: { 
    "Content-Type": "application/json",
    "X-Mobile-Client": isMobile().toString()
  },
  timeout: isMobile() ? 30000 : 10000, // Longer timeout for mobile
});

// Request interceptor: attach JWT token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor: handle 401 and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem("refresh_token");

      if (refreshToken) {
        try {
          const resp = await axios.post(`${API_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          const { access_token, refresh_token: newRefresh } = resp.data;
          localStorage.setItem("access_token", access_token);
          localStorage.setItem("refresh_token", newRefresh);
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return api(originalRequest);
        } catch {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      } else {
        localStorage.removeItem("access_token");
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

// --- Auth ---
export const authAPI = {
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }),
  register: (email: string, password: string, full_name: string) =>
    api.post("/auth/register", { email, password, full_name }),
  getGoogleUrl: () => api.get("/auth/google/url"),
  googleCallback: (code: string) =>
    api.post("/auth/google/callback", { code }),
  getMe: () => api.get("/auth/me"),
  updateMe: (data: {
    full_name?: string;
    avatar_url?: string;
    venmo_link?: string;
  }) => api.put("/auth/me", data),
  refresh: (refresh_token: string) =>
    api.post("/auth/refresh", { refresh_token }),
};

// --- Admin ---
export const adminAPI = {
  getStats: () => api.get("/admin/stats"),
  listUsers: (params?: {
    role?: string;
    search?: string;
    skip?: number;
    limit?: number;
  }) => api.get("/admin/users", { params }),
  createUser: (data: {
    email: string;
    password: string;
    full_name: string;
    role: string;
  }) => api.post("/admin/users", data),
  updateUser: (
    userId: number,
    data: {
      full_name?: string;
      is_active?: boolean;
      role?: string;
      coach_id?: number;
    }
  ) => api.put(`/admin/users/${userId}`, data),
  deleteUser: (userId: number) => api.delete(`/admin/users/${userId}`),
  listContacts: (unreadOnly?: boolean) =>
    api.get("/admin/contacts", { params: { unread_only: unreadOnly } }),
  markContactRead: (contactId: number) =>
    api.put(`/admin/contacts/${contactId}/read`),
  downloadBackup: () =>
    api.get("/admin/backup", { responseType: "blob" }),
};

// --- Coach ---
export const coachAPI = {
  listAthletes: () => api.get("/coach/athletes"),
  listUsers: (params?: {
    role?: string;
    search?: string;
    only_unlinked?: boolean;
    skip?: number;
    limit?: number;
  }) => api.get("/coach/users", { params }),
  linkAthlete: (athleteId: number) =>
    api.post(`/coach/athletes/${athleteId}/link`),
  unlinkAthlete: (athleteId: number) =>
    api.post(`/coach/athletes/${athleteId}/unlink`),
  checkAthleteConnection: (athleteId: number) =>
    api.get(`/coach/athletes/${athleteId}/check-connection`),
  getWorkouts: (workoutType?: string) =>
    api.get("/coach/workouts", { params: { workout_type: workoutType } }),
  shareWorkouts: (garminWorkoutIds: string[], athleteId: number) =>
    api.post("/coach/share-workouts", {
      garmin_workout_ids: garminWorkoutIds,
      athlete_id: athleteId,
    }),
  listSharedWorkouts: (athleteId?: number) =>
    api.get("/coach/shared-workouts", { params: { athlete_id: athleteId } }),
};

// --- Athlete ---
export const athleteAPI = {
  listCoaches: () => api.get("/athlete/coaches"),
  selectCoach: (coachId: number) =>
    api.post(`/athlete/select-coach/${coachId}`),
  getWorkouts: () => api.get("/athlete/workouts"),
  importWorkouts: (sharedWorkoutIds: number[]) =>
    api.post("/athlete/workouts/import", {
      shared_workout_ids: sharedWorkoutIds,
    }),
  removeWorkout: (sharedWorkoutId: number) =>
    api.delete(`/athlete/workouts/${sharedWorkoutId}`),
};

// --- Garmin ---
export const garminAPI = {
  connect: (garminEmail: string, garminPassword: string) =>
    api.post("/garmin/connect", {
      garmin_email: garminEmail,
      garmin_password: garminPassword,
    }),
  getStatus: () => api.get("/garmin/status"),
  testConnection: () => api.post("/garmin/test"),
  disconnect: () => api.delete("/garmin/disconnect"),
};

// --- Public ---
export const publicAPI = {
  submitContact: (data: {
    name: string;
    email: string;
    phone?: string;
    message: string;
  }) => api.post("/public/contact", data),
};

// --- Messages ---
export const messageAPI = {
  send: (data: { recipient_id: number; subject?: string; body: string }) =>
    api.post("/messages/send", data),
  getInbox: (params?: { unread_only?: boolean; skip?: number; limit?: number }) =>
    api.get("/messages/inbox", { params }),
  getSent: (params?: { skip?: number; limit?: number }) =>
    api.get("/messages/sent", { params }),
  markRead: (messageId: number) =>
    api.put(`/messages/${messageId}/read`),
  listRecipients: () => api.get("/messages/coaches"),
};

export default api;
