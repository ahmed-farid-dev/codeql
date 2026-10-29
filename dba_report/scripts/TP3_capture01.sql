set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

conn / as sysdba
show parameter spfile
select name, value from v$parameter where name = 'processes';
select name, value from v$spparameter where name = 'processes';
alter system set processes = 300 scope = spfile;
select name, value from v$parameter where name = 'processes';
select name, value from v$spparameter where name = 'processes';
