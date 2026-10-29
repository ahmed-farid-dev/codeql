set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter session set container = CDB$ROOT;
alter database datafile '&DIR\data01.dbf' resize 11m;
select file_name, bytes/1024/1024 mb from dba_data_files where tablespace_name = 'DATA01';
alter session set container = PDB1;
alter database default tablespace tbs1;
select property_name, property_value from database_properties where property_name like 'DEFAULT%TABLESPACE';
select tablespace_name, contents, status from dba_tablespaces;
