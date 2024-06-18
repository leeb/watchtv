pkgdatadir = get_option('prefix') / get_option('datadir') / meson.project_name()
moduledir = pkgdatadir / 'watchtv'
gnome = import('gnome')

gnome.compile_resources('watchtv',
  'watchtv.gresource.xml',
  gresource_bundle: true,
  install: true,
  install_dir: pkgdatadir,
)

python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').full_path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', get_option('prefix') / get_option('localedir'))
conf.set('pkgdatadir', pkgdatadir)

configure_file(
  input: 'watchtv.in',
  output: 'watchtv',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir'),
  install_mode: 'r-xr-xr-x'
)

watchtv_sources = [
  '__init__.py',
  'main.py',
  'window.py',
  'channels.py',
  'videosize.py',
  'gstflags.py',
  'settings.py',
  'preferences.py',
  'tvhapi.py',
]

install_data(watchtv_sources, install_dir: moduledir)
