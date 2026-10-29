set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

col name format a60
col member format a60
select name, status from v$controlfile;
select file#, name, status, bytes/1024/1024 mb from v$datafile;
select ts#, name, bigfile from v$tablespace;
select group#, type, member, status from v$logfile;
