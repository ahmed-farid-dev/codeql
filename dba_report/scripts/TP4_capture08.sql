set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter session set container = PDB1;
show con_name
create tablespace tbs1 datafile '&PDBDIR\tbs1.dbf' size 5m autoextend on next 1m maxsize 100m;
select tablespace_name, file_name, bytes/1024/1024 mb, autoextensible, increment_by, maxbytes/1024/1024 max_mb from dba_data_files where tablespace_name = 'TBS1';
