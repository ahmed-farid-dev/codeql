set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl
accept SYSPWD hide prompt 'SYS password: '

conn sys/&SYSPWD@pdborcl as sysdba
alter system enable restricted session;
select name, open_mode, restricted from v$pdbs;
conn hr/hr@pdborcl
conn sys/&SYSPWD@pdborcl as sysdba
alter system disable restricted session;
conn hr/hr@pdborcl
show user
