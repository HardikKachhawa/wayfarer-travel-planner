create table if not exists public.trips (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  request jsonb not null,
  itinerary jsonb not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists trips_user_idx on public.trips(user_id, updated_at desc);

alter table public.trips enable row level security;
create policy "own trips: read"   on public.trips for select using (auth.uid() = user_id);
create policy "own trips: insert" on public.trips for insert with check (auth.uid() = user_id);
create policy "own trips: update" on public.trips for update using (auth.uid() = user_id);
create policy "own trips: delete" on public.trips for delete using (auth.uid() = user_id);
