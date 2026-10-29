set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

select instance_name from v$instance;
select name, cdb from v$database;
show con_name
select con_id, pdb_name, status from dba_pdbs;
show pdbs
select con_id, name, open_mode, restricted from v$pdbs;
