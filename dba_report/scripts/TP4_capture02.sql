set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

alter system set control_files='&DIR\control01.ctl','&DIR\control02.ctl','&DIR\control04.ctl' scope=spfile;
shutdown immediate
host copy &DIR\control01.ctl &DIR\control04.ctl
startup
select name from v$controlfile;
