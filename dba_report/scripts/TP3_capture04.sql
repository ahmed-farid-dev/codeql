set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

shutdown immediate
startup
select name, value from v$parameter where name = 'open_cursors';
select name, value from v$spparameter where name = 'open_cursors';
select name, value from v$system_parameter where name = 'open_cursors';
