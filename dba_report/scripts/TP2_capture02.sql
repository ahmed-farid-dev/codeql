set echo on linesize 180 pagesize 50 verify off feedback on
define DIR=C:\app\yourNAME\oradata\orcl
define PDBDIR=C:\app\yourNAME\oradata\orcl\pdborcl

shutdown immediate
create pfile='path\orcl\PFILE\init1.ora' from spfile='C:\app\yourNAME\product\12.1.0\dbhome_1\database\SPFILEORCL.ORA';
host dir path\orcl\PFILE\init1.ora
startup pfile='path\orcl\PFILE\init1.ora'
select instance_name, status from v$instance;
show parameter spfile
