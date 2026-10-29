set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

conn / as sysdba
show parameter control_files
select name from v$controlfile;
select value from v$parameter where name = 'control_files';
select type, record_size, records_total, records_used, record_size*records_total as section_bytes from v$controlfile_record_section where type = 'DATAFILE';
