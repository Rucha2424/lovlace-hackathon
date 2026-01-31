const API_BASE = '/api';

export async function getTopology() {
  const r = await fetch(`${API_BASE}/topology`);
  if (!r.ok) throw new Error('Failed to fetch topology');
  return r.json();
}

export async function getTraffic() {
  const r = await fetch(`${API_BASE}/traffic`);
  if (!r.ok) throw new Error('Failed to fetch traffic');
  return r.json();
}

export async function getDashboard() {
  const r = await fetch(`${API_BASE}/dashboard`);
  if (!r.ok) throw new Error('Failed to fetch dashboard');
  return r.json();
}

export async function getCapacity(withBuffer = true) {
  const r = await fetch(`${API_BASE}/capacity?with_buffer=${withBuffer}`);
  if (!r.ok) throw new Error('Failed to fetch capacity');
  return r.json();
}

export async function getReports() {
  const r = await fetch(`${API_BASE}/reports`);
  if (!r.ok) throw new Error('Failed to fetch reports');
  return r.json();
}

export async function processData() {
  const r = await fetch(`${API_BASE}/process`, { method: 'POST' });
  if (!r.ok) throw new Error('Failed to process data');
  return r.json();
}
