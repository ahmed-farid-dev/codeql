set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

col tablespace_name format a18
col file_name format a60
select tablespace_name, contents, status, block_size, extent_management, segment_space_management from dba_tablespaces;
select tablespace_name, file_name, bytes/1024/1024 mb, autoextensible from dba_data_files;
select tablespace_name, file_name, bytes/1024/1024 mb from dba_temp_files;
