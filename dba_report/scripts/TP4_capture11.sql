set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter session set container = CDB$ROOT;
drop tablespace idx03 including contents and datafiles;
alter tablespace idx02 add datafile '&DIR\idx02b.dbf' size 5m;
select tablespace_name, file_name from dba_data_files where tablespace_name like 'IDX%';
select tablespace_name, status from dba_tablespaces where tablespace_name = 'IDX02';
alter tablespace idx02 offline;
select tablespace_name, status from dba_tablespaces where tablespace_name = 'IDX02';
alter tablespace idx02 online;
select tablespace_name, status from dba_tablespaces where tablespace_name = 'IDX02';
