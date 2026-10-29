set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

conn / as sysdba
create tablespace data01 datafile '&DIR\data01.dbf' size 10m;
create tablespace idx02 datafile '&DIR\idx02.dbf' size 5m;
create tablespace idx03 datafile '&DIR\idx03.dbf' size 5m;
create temporary tablespace temp01 tempfile '&DIR\temp01.dbf' size 10m;
create undo tablespace undotbs02 datafile '&DIR\undotbs02.dbf' size 20m;
select tablespace_name, contents, status from dba_tablespaces;
