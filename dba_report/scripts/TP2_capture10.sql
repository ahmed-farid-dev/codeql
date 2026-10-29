set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

ALTER PLUGGABLE DATABASE ALL OPEN READ WRITE;
select name, open_mode from v$pdbs;
ALTER PLUGGABLE DATABASE pdbCS CLOSE IMMEDIATE;
select name, open_mode from v$pdbs;
ALTER PLUGGABLE DATABASE pdbCS OPEN;
select name, open_mode from v$pdbs;
ALTER PLUGGABLE DATABASE ALL EXCEPT pdbCS CLOSE IMMEDIATE;
select name, open_mode from v$pdbs;
