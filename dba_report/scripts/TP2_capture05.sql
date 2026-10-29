set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter session set container = pdborcl;
show con_name
select name, open_mode from v$pdbs;
-- if the PDB is MOUNTED: open it read write; if already READ WRITE skip this line
-- alter pluggable database open read write;
select name, open_mode from v$pdbs;
alter pluggable database close immediate;
alter pluggable database open read only;
select name, open_mode from v$pdbs;
