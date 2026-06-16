import API from './client';

// ── Auth ──────────────────────────────────────────────────────────────────────
export const register = (data)   => API.post('/api/auth/register', data);
export const login    = (data)   => API.post('/api/auth/login', data);
export const logout   = ()       => API.post('/api/auth/logout');
export const refresh  = ()       => API.post('/api/auth/refresh');

// ── User ──────────────────────────────────────────────────────────────────────
export const getMe            = ()       => API.get('/api/users/me');
export const updateMe         = (data)   => API.put('/api/users/me', data);
export const getMyStats       = ()       => API.get('/api/users/me/stats');
export const updateConditions = (conds)  => API.patch('/api/users/me/conditions', conds);
export const getSafetyAudit   = ()       => API.get('/api/users/me/safety-audit');

// ── Exercises ─────────────────────────────────────────────────────────────────
export const getExercises  = (params) => API.get('/api/exercises', { params });
export const getExercise   = (id)     => API.get(`/api/exercises/${id}`);
export const searchExercises = (q)    => API.get('/api/exercises/search', { params: { q } });
export const getCategories = ()       => API.get('/api/exercises/categories');

// ── Recommendations ───────────────────────────────────────────────────────────
export const getRecommendations   = (userId, topN = 6) =>
  API.get(`/api/recommendations/${userId}`, { params: { top_n: topN } });
export const getSafetyRules       = (userId) =>
  API.get(`/api/recommendations/${userId}/safety-rules`);
export const getRecommendHistory  = (userId) =>
  API.get(`/api/recommendations/${userId}/history`);

// ── Logs ──────────────────────────────────────────────────────────────────────
export const createLog  = (data)   => API.post('/api/logs', data);
export const getLogs    = (userId) => API.get(`/api/logs/${userId}`);
export const getLogStats = (userId) => API.get(`/api/logs/${userId}/stats`);

// ── Rewards ───────────────────────────────────────────────────────────────────
export const getRewards        = (userId) => API.get(`/api/rewards/${userId}`);
export const evaluateRewards   = (userId) => API.post(`/api/rewards/evaluate/${userId}`);
export const getAvailableBadges = (userId) => API.get(`/api/rewards/${userId}/available-badges`);
export const getLeaderboard    = ()        => API.get('/api/rewards/leaderboard/top');
