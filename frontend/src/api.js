const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const getTasks = () => request('/tasks');

export const getTask = (id) => request(`/tasks/${id}`);

export const createTask = (data) =>
  request('/tasks', { method: 'POST', body: JSON.stringify(data) });

export const updateTask = (id, data) =>
  request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(data) });

export const deleteTask = (id) =>
  request(`/tasks/${id}`, { method: 'DELETE' });
