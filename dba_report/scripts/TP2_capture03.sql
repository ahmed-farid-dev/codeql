set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

col username format a15
col program format a35
col machine format a20
select sid, serial#, username, status, machine, program from v$session order by username;
