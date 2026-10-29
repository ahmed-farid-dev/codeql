set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

conn / as sysdba
shutdown immediate
startup
show pdbs
ALTER PLUGGABLE DATABASE pdbCS OPEN READ WRITE;
show pdbs
