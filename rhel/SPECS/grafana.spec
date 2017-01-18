%global debug_package   %{nil}
%global provider        github
%global provider_tld    com
%global project         grafana
%global repo            grafana
# https://github.com/grafana/grafana
%global import_path     %{provider}.%{provider_tld}/%{project}/%{repo}
%global commit          v4.0.2
%global shortcommit     %(c=%{commit}; echo ${c:0:7})

%if ! 0%{?gobuild:1}
%define gobuild(o:) go build -ldflags "${LDFLAGS:-} -B 0x$(head -c20 /dev/urandom|od -An -tx1|tr -d ' \\n')" -a -v -x %{?**}; 
%endif

Name:           grafana
Version:        4.0.2
Release:        2%{?dist}
Summary:        Grafana is an open source, feature rich metrics dashboard and graph editor
License:        ASL 2.0
URL:            https://%{import_path}
Source0:        https://%{import_path}/archive/%{commit}/%{repo}-%{shortcommit}.tar.gz
Source1:        grafana-node_modules-%{shortcommit}.el6.tar.gz
Source2:        grafana-node_modules-%{shortcommit}.el7.tar.gz
Source3:        grafana-server.service
ExclusiveArch:  %{ix86} x86_64 %{arm}

BuildRequires: golang >= 1.7.3
BuildRequires: nodejs-grunt-cli fontconfig

%if 0%{?fedora} || 0%{?rhel} == 7
BuildRequires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

#Requires:       golang >= 1.7.3

%description
Grafana is an open source, feature rich metrics dashboard and graph editor for
Graphite, InfluxDB & OpenTSDB.

%prep
%if 0%{?rhel} == 6
%setup -q -b 1 -n %{repo}-%{version}
%else
%setup -q -b 2 -n %{repo}-%{version}
%endif
rm -rf Godeps

%build
mkdir -p _build/src
mv vendor/github.com _build/src/
mv vendor/golang.org _build/src/
mv vendor/gopkg.in   _build/src/

mkdir -p ./_build/src/github.com/grafana
ln -s $(pwd) ./_build/src/github.com/grafana/grafana
export GOPATH=$(pwd)/_build:%{gopath}

%gobuild -o ./bin/grafana-server ./pkg/cmd/grafana-server
%gobuild -o ./bin/grafana-cli ./pkg/cmd/grafana-cli
/usr/bin/node --max-old-space-size=4500 /usr/bin/grunt --verbose release
#/usr/bin/node --max-old-space-size=4500 /usr/bin/grunt --verbose jshint:source jshint:tests jscs tslint clean:release copy:node_modules copy:public_to_gen phantomjs css htmlmin:build ngtemplates cssmin:build ngAnnotate:build concat:js filerev remapFilerev usemin uglify:genDir build-post-process compress:release

%install
# install -d -p %{buildroot}/%{gopath}/src/%{import_path}/
# cp -pav *.go %{buildroot}/%{gopath}/src/%{import_path}/
# cp -rpav pkg public conf tests %{buildroot}/%{gopath}/src/%{import_path}/
install -d -p %{buildroot}%{_datadir}/%{name}
cp -pav *.md %{buildroot}%{_datadir}/%{name}
# cp -rpav benchmarks %{buildroot}/%{gopath}/src/%{import_path}/
cp -rpav docs %{buildroot}%{_datadir}/%{name}
cp -rpav public_gen %{buildroot}%{_datadir}/%{name}/public
cp -rpav scripts %{buildroot}%{_datadir}/%{name}
cp -rpav vendor %{buildroot}%{_datadir}/%{name}
install -d -p %{buildroot}%{_sbindir}
cp bin/%{name}-server %{buildroot}%{_sbindir}/
install -d -p %{buildroot}%{_bindir}
cp bin/%{name}-cli %{buildroot}%{_bindir}/
install -d -p %{buildroot}%{_sysconfdir}/%{name}
cp conf/sample.ini %{buildroot}%{_sysconfdir}/%{name}/grafana.ini
mv conf/ldap.toml %{buildroot}%{_sysconfdir}/%{name}/
cp -rpav conf %{buildroot}%{_datadir}/%{name}
%if 0%{?fedora} || 0%{?rhel} == 7
mkdir -p %{buildroot}/usr/lib/systemd/system
install -p -m 0644 %{SOURCE3} %{buildroot}/usr/lib/systemd/system/
%else
mkdir -p %{buildroot}%{_initddir}/
install -p -m 0644 packaging/rpm/init.d/grafana-server %{buildroot}%{_initddir}/
%endif
#mkdir -p %{buildroot}%{_sysconfdir}/sysconfig
#install -p -m 0644 packaging/rpm/sysconfig/grafana-server %{buildroot}%{_sysconfdir}/sysconfig
install -d -p %{buildroot}%{_sharedstatedir}/%{name}
install -d -p %{buildroot}/var/log/%{name}

%check
export GOPATH=$(pwd)/_build:%{gopath}
go test ./pkg/api
go test ./pkg/bus
go test ./pkg/components/apikeygen
go test ./pkg/components/renderer
go test ./pkg/events
go test ./pkg/models
go test ./pkg/plugins
go test ./pkg/services/sqlstore
go test ./pkg/services/sqlstore/migrations
go test ./pkg/setting
go test ./pkg/util

%files
%defattr(-, grafana, grafana, -)
%{_datadir}/%{name}
%exclude %{_datadir}/%{name}/*.md
%exclude %{_datadir}/%{name}/docs
%doc %{_datadir}/%{name}/CHANGELOG.md
%doc %{_datadir}/%{name}/LICENSE.md
%doc %{_datadir}/%{name}/NOTICE.md
%doc %{_datadir}/%{name}/README.md
%doc %{_datadir}/%{name}/docs
%attr(0755, root, root) %{_sbindir}/%{name}-server
%attr(0755, root, root) %{_bindir}/%{name}-cli
%{_sysconfdir}/%{name}/grafana.ini
%{_sysconfdir}/%{name}/ldap.toml
%if 0%{?fedora} || 0%{?rhel} == 7
%attr(-, root, root) /usr/lib/systemd/system/grafana-server.service
%else
%attr(-, root, root) %{_initddir}/grafana-server
%endif
#attr(-, root, root) %{_sysconfdir}/sysconfig/grafana-server
%dir %{_sharedstatedir}/%{name}
%dir /var/log/%{name}

%pre
getent group grafana >/dev/null || groupadd -r grafana
getent passwd grafana >/dev/null || \
    useradd -r -g grafana -d /etc/grafana -s /sbin/nologin \
    -c "Grafana Dashboard" grafana
exit 0

%post
%systemd_post grafana.service

%preun
%systemd_preun grafana.service

%postun
%systemd_postun grafana.service

%changelog
* Thu Dec 29 2016 Mykola Marzhan <mykola.marzhan@percona.com> - 4.0.2-2
- use fixed grafana-server.service

* Thu Dec 15 2016 Mykola Marzhan <mykola.marzhan@percona.com> - 4.0.2-1
- up to 4.0.2

* Fri Jul 31 2015 Graeme Gillies <ggillies@redhat.com> - 2.0.2-3
- Unbundled phantomjs from grafana

* Tue Jul 28 2015 Lon Hohberger <lon@redhat.com> - 2.0.2-2
- Change ownership for grafana-server to root

* Tue Apr 14 2015 Graeme Gillies <ggillies@redhat.com> - 2.0.2-1
- First package for Fedora