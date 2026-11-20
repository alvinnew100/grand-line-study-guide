-- Study guide accounts: username + password, used only to sync study progress.
-- Run once in the Supabase dashboard: SQL Editor -> New query -> paste -> Run.
create extension if not exists pgcrypto with schema extensions;

create table if not exists public.study_accounts (
  username   text primary key check (username ~ '^[a-z0-9_]{3,20}$'),
  pass_hash  text not null,
  data       jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);
create table if not exists public.study_sessions (
  token_hash text primary key,
  username   text not null references public.study_accounts(username) on delete cascade,
  created_at timestamptz not null default now()
);
-- Row Level Security on with no policies: the tables can only be reached through the functions below.
alter table public.study_accounts enable row level security;
alter table public.study_sessions enable row level security;
revoke all on public.study_accounts, public.study_sessions from anon, authenticated;

create or replace function public.sg_new_session(p_username text) returns text
language plpgsql security definer set search_path = public, extensions as $$
declare t text := encode(gen_random_bytes(24), 'hex');
begin
  insert into study_sessions(token_hash, username) values (encode(digest(t, 'sha256'), 'hex'), p_username);
  return t;
end $$;

create or replace function public.sg_register(p_username text, p_password text) returns text
language plpgsql security definer set search_path = public, extensions as $$
begin
  if p_username !~ '^[a-z0-9_]{3,20}$' then raise exception 'Username must be 3-20 characters using a-z, 0-9 or _'; end if;
  if length(p_password) < 6 or length(p_password) > 72 then raise exception 'Password must be 6-72 characters'; end if;
  if (select count(*) from study_accounts) >= 500 then raise exception 'Sign-ups are closed'; end if;
  begin
    insert into study_accounts(username, pass_hash) values (p_username, crypt(p_password, gen_salt('bf', 10)));
  exception when unique_violation then
    raise exception 'That username is taken';
  end;
  return sg_new_session(p_username);
end $$;

create or replace function public.sg_login(p_username text, p_password text) returns text
language plpgsql security definer set search_path = public, extensions as $$
declare h text;
begin
  perform pg_sleep(0.4);  -- slows password guessing
  select pass_hash into h from study_accounts where username = p_username;
  if h is null or crypt(p_password, h) <> h then raise exception 'Wrong username or password'; end if;
  return sg_new_session(p_username);
end $$;

create or replace function public.sg_user(p_username text, p_token text) returns text
language sql security definer set search_path = public, extensions stable as $$
  select username from study_sessions
  where username = p_username and token_hash = encode(digest(p_token, 'sha256'), 'hex');
$$;

create or replace function public.sg_load(p_username text, p_token text) returns jsonb
language plpgsql security definer set search_path = public, extensions as $$
begin
  if sg_user(p_username, p_token) is null then raise exception 'Session expired, please log in again'; end if;
  return (select data from study_accounts where username = p_username);
end $$;

create or replace function public.sg_save(p_username text, p_token text, p_data jsonb) returns timestamptz
language plpgsql security definer set search_path = public, extensions as $$
begin
  if sg_user(p_username, p_token) is null then raise exception 'Session expired, please log in again'; end if;
  if pg_column_size(p_data) > 3000000 then raise exception 'Progress data is too large'; end if;
  update study_accounts set data = p_data, updated_at = now() where username = p_username;
  return now();
end $$;

create or replace function public.sg_logout(p_username text, p_token text) returns void
language sql security definer set search_path = public, extensions as $$
  delete from study_sessions where username = p_username and token_hash = encode(digest(p_token, 'sha256'), 'hex');
$$;

revoke all on function public.sg_new_session(text), public.sg_user(text, text) from public, anon, authenticated;
grant execute on function public.sg_register(text, text), public.sg_login(text, text), public.sg_load(text, text),
  public.sg_save(text, text, jsonb), public.sg_logout(text, text) to anon, authenticated;
notify pgrst, 'reload schema';

-- Public leaderboard: username plus the stats each client reports (points, problems, lessons, streak).
create or replace function public.sg_leaderboard() returns table(username text, stats jsonb)
language sql security definer set search_path = public stable as $$
  select a.username, a.data->'_stats'
  from study_accounts a
  where jsonb_typeof(a.data->'_stats'->'points') = 'number'
  order by (a.data->'_stats'->>'points')::numeric desc, a.updated_at asc
  limit 100;
$$;
grant execute on function public.sg_leaderboard() to anon, authenticated;
notify pgrst, 'reload schema';

-- Used by the "judge" Edge Function to confirm a caller is logged in.
create or replace function public.sg_check(p_username text, p_token text) returns boolean
language sql security definer set search_path = public, extensions stable as $$
  select exists (select 1 from study_sessions
                 where username = p_username and token_hash = encode(digest(p_token, 'sha256'), 'hex'));
$$;
grant execute on function public.sg_check(text, text) to anon, authenticated;
notify pgrst, 'reload schema';
