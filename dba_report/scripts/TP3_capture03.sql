set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

select name, value from v$parameter where name = 'open_cursors';
select name, value from v$spparameter where name = 'open_cursors';
select name, value from v$system_parameter where name = 'open_cursors';
alter system set open_cursors = 400 scope = memory;
select name, value from v$parameter where name = 'open_cursors';
select name, value from v$spparameter where name = 'open_cursors';
select name, value from v$system_parameter where name = 'open_cursors';
