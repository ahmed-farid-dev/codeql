set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

create tablespace tbs_multi datafile '&PDBDIR\multi1.dbf' size 5m, '&PDBDIR\multi2.dbf' size 5m;
select tablespace_name, file_name from dba_data_files where tablespace_name = 'TBS_MULTI';
create table t_demo (id number, name varchar2(30)) tablespace tbs_multi;
select table_name, tablespace_name from user_tables where table_name = 'T_DEMO';
