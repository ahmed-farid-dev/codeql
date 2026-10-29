set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

conn / as sysdba
show user
select instance_name as sid, status from v$instance;
select name, type, value as path from v$parameter where name = 'spfile';
select instance_name, to_char(startup_time,'DD/MM/YYYY HH24:MI:SS') startup_time from v$instance;
