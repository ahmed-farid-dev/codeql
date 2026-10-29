set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter database add logfile member '&DIR\redolog02.log' to group 1;
alter database add logfile group 4 ('&DIR\redo04a.log') size 50m;
select group#, member, status from v$logfile order by group#;
alter database drop logfile group 4;
alter system checkpoint;
alter database drop logfile member '&DIR\redolog01.log';
select group#, member, status from v$logfile order by group#;
