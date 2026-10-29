set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter system set open_cursors = 350 scope = both;
alter system set job_queue_processes = 20 scope = memory;
alter system set undo_retention = 1200 scope = spfile;
col name format a22
col value format a12
select p.name, p.value running, s.value in_spfile from v$parameter p, v$spparameter s where p.name = s.name and p.name in ('open_cursors','job_queue_processes','undo_retention','processes');
-- revert everything done in the SPFILE
alter system reset open_cursors scope = spfile;
alter system reset undo_retention scope = spfile;
alter system reset processes scope = spfile;
alter system set open_cursors = 300 scope = memory;
alter system set job_queue_processes = 1000 scope = memory;
select name, value, isdefault from v$spparameter where name in ('open_cursors','undo_retention','processes');
