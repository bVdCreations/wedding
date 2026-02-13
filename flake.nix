{
  description = "wedding development environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          packages = with pkgs; [
            nodejs_24
            pnpm_9
            playwright-driver.browsers

            uv
            libgcc # needed for sqlalchemy
          ];

          shellHook = ''
            export PLAYWRIGHT_BROWSERS_PATH="${pkgs.playwright-driver.browsers}"
            export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS="true"
            export PLAYWRIGHT_NODEJS_PATH="${pkgs.nodejs_24}/bin/node"
            export PATH="$HOME/.local/bin:$PATH" # access to lsp binary for neovim
            export LD_LIBRARY_PATH="${pkgs.stdenv.cc.cc.lib}/lib"
          '';
        };
      }
    );
}
