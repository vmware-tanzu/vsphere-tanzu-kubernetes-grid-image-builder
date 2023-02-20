Name: photon_vasecurity
Summary: VA Security Hardening scripts for VMware
Version: %{version}
Release: %{release}
License: VMware License
Vendor: VMware, Inc.
BuildRoot: %{_topdir}/INSTALL
Group: Applications/System
BuildArch: noarch
AutoReqProv: no
#Obsoletes: tcpdump

%description
Virtual Appliance Security Hardening for Photon.

%prep


%clean

%install
mkdir -p %{buildroot}/vasecurity
cp -rf %{_topdir}/SOURCES/vasecurity/* %{buildroot}/vasecurity/

%files
%defattr(0700,root,root)
/vasecurity

# ----------------------------------------------------------------------
# This is the pre install script. It is also used for updates.
# ----------------------------------------------------------------------
%pre

# ----------------------------------------------------------------------
# This is the post install/update script
# ----------------------------------------------------------------------
%post
/vasecurity/postinstall

# ----------------------------------------------------------------------
# This is the pre uninstall script
# ----------------------------------------------------------------------
%preun

# ----------------------------------------------------------------------
# This is the post uninstall script, need to specify all dirs as
# there may be other packages installing under /opt/maas.
# ----------------------------------------------------------------------
%postun
