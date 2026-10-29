set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

select name, log_mode from v$database;
archive log list
shutdown immediate
startup mount
alter database archivelog;
alter database open;
host mkdir C:\archives
alter system set log_archive_dest_1='LOCATION=C:\archives' scope=both;
alter system switch logfile;
alter system switch logfile;
archive log list
select sequence#, name, completion_time from v$archived_log order by sequence#;
host dir C:\archives
