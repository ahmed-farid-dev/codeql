set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

select name from v$controlfile;
show parameter memory_target
show parameter memory_max_target
select name, description from v$bgprocess where paddr <> '00' order by name;
select dbid, name, created, log_mode, open_mode from v$database;
