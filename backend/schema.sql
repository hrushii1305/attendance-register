create table students (
  id         bigint generated always as identity primary key,
  name       text not null,
  created_at timestamptz not null default now()
);

create table attendance (
  id         bigint generated always as identity primary key,
  student_id bigint not null references students(id) on delete cascade,
  date       date not null,
  present    boolean not null,
  unique (student_id, date)
);

alter table students   enable row level security;
alter table attendance enable row level security;
-- No policies on purpose. The publishable key (which is in the browser) can
-- then read or write nothing. The secret key that FastAPI uses skips these
-- checks, which enforces "only FastAPI talks to the database".
