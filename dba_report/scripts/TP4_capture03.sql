set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

col member format a60
select group#, member, type, status from v$logfile order by group#;
select group#, thread#, sequence#, bytes/1024/1024 as mb, members, status, archived from v$log;
