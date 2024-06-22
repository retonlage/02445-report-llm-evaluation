{
  inputs.new-nixpkgs = { # for julia
    url = "github:NixOS/nixpkgs/23.11";
  };
  inputs.newest-nixpkgs = { # for typst
    url = "github:NixOS/nixpkgs/24.05";
  };
  outputs = {new-nixpkgs, newest-nixpkgs, ...}:  let
  pkgs = (import new-nixpkgs) {
    system = "x86_64-linux";
  };
  new-pkgs = (import newest-nixpkgs) {
    system = "x86_64-linux";
  };

  myPython = pkgs.python311;

  pythonWithPkgs = myPython.withPackages (pythonPkgs: with pythonPkgs; [
    ipython
    pip
    setuptools
    virtualenvwrapper
    wheel
  ]);

  lib-path = with pkgs; lib.makeLibraryPath [
    libffi
    openssl
    stdenv.cc.cc
    zlib
    # linuxPackages.nvidia_x11 # for cuda
  ];

  shell = pkgs.mkShell {
    buildInputs = [
      pythonWithPkgs
      pkgs.julia
      (new-pkgs.typst)

      pkgs.readline
      pkgs.libffi
      pkgs.openssl

      # unfortunately needed because of messing with LD_LIBRARY_PATH below
      pkgs.git
      pkgs.openssh
      pkgs.rsync
    ];

    shellHook = ''
      # Allow the use of wheels.
      SOURCE_DATE_EPOCH=$(date +%s)
      # Augment the dynamic linker path
      export "LD_LIBRARY_PATH=$LD_LIBRARY_PATH:${lib-path}"
      # Setup the virtual environment if it doesn't already exist.
      VENV=.venv
      if test ! -d $VENV; then
        virtualenv $VENV
      fi
      source ./$VENV/bin/activate
      export PYTHONPATH=`pwd`/$VENV/${myPython.sitePackages}/:$PYTHONPATH
    '';
  };
  in
    {
      devShells."x86_64-linux".default = shell;
    };
}
