{pkgs}: {
  deps = [
    pkgs.glibcLocales
    pkgs.libxcrypt
    pkgs.postgresql
    pkgs.openssl
  ];
}
