# dev-workflow
This is a simple set of scripts to manage git repos and a prompt generator for zshrc. This workflow is based around having an internal\self hosted git server as well as a mirror of that work one something like Github where the polished work is located. These scripts and the prompt generator provided allow setting the remotes back and forth without having to remember URLs as well as rendering the information back to the user.

```
An example of the output on the prompt:
lucia@athena git:(master\gitea\prod) ✅

or for a dev project:
lucia@dev-workflow git:(master\gitea\mvp) ❌
```

You can think of this as something similar to starfish (https://starship.rs/) or ohmyzsh (https://ohmyz.sh/) rather this is hyperspecific to my usecase\dev workflow. I have used both of these and think fairly high of them, I just didn't want to write a customization\modification or a plugin for them for this specific workflow and I didn't want the overhead of loading things I do not need within the binary.

Note, I fully expect most people to not need this, but it works well for me because I rapidly prototype and build projects across a nontrivial number of codebases in my spare time. Partly because I find it fun and partly to better my quality of life.

## Why
I have been a programmer since I was 14...I am 31...I have a lot of projects over that time I have written and keeping track of them is somewhat of a mess. My estimates is that the projects are probably somewhere in the few hundred. For context around 86 of these are currently stored in Gitea as projects I care about (depending on when this repo was uploaded this number maybe very off). And while monorepos do help with this...they don't address the issue if the projects are completely different areas.

I also do not like being dependent on an external service for my developer workflow so I have for years maintained an internal git repo for my personal projects. This is partly because I want a clean divide on what is a test\prototype bit of code and what is something that I feel comfortable having on my Github that will show more professionally. In my opinion...polishing a bit of code to the point it can be publicly shared makes very little since if you are not going to use in the long term. Additionally, this seperation allows me to more easily test code and use internal CI\CD which keeps my costs down and keeps the public mirror clean.

If I find a project is good enough and is being used by me with regularity then I open source it and move it onto Github. Sometimes this is after a few hours of use (if it was to replace something specific to me), sometimes a few weeks, and sometimes a few months. Typically at this point I go through and add the LICENSE, update the README to reflect the current state, cleanup the code, and remove any hardcoded variables; these are often not because time and rapid prototyping of ideas.

This same rapid prototyping has also resulted in a workflow where I have a dev scratchspace that I clone random repos, test things, and archive it periodically once it becomes too messy. Additionally, this scratchspace is also home to randomly cloned open source projects I am doing analysis on. Once a project is usable\stable it migrates from scratchspace to Gitea. Alongside the scratchspace is a clean repo with only currently worked on projects that are at least MVP. Everything in this folder is stored in Gitea and may or may not be stored in Github depending on it's state. These projects are typically in one of a couple states:
* Homelab_Infra_Public: Project is on accessible on the internal Gitea repo and viewable to everyone on the local network (I am fine with people seeing prototypes)
* Homelab_Infra_Prod: Project is on Github and has been cleaned up\documented to a degree it can be publicly shared...it may even have a blog post written about it.

The internal gitea repo also has multiple mirrors. These mirrors are used for local builds or for analysis of changes when debugging issues. For context...I have had to read the source for: Mesa, K8s, and the Linux kernel over the years as well as multiple open source projects I use. Some of these mirrors I want to keep backed up, but others like the Linux kernel I do not need to. Backing up the entire set of repos would be a terrible waste of space so I needed a way to only update what I needed.

Lastly...most shell prompt generators available off of the shelf work off of a plugin system and may even be written in a language that is not incredibly high performance so under heavy plugin usage is can slow down your shell. I also didn't want to write a plugin for my specific workflow that was so specific to me it would likely remain out of tree. And even if I did I would still deal with the overhead of loading a prompt generator that is way more complex than I actually need that would add small delays to my shell operations and these add up over time\result in just that little break of a developer flow.

## How it works
The file `main.py` performs a clone or pull on all git repos unless excluded (this is a substring search), you can optionally partly overwrite a conclusion which allows you to say ignore all mirrors, but include a specific one you would like to keep backed up.

This same file also generates a JSON file that is used by the prompt generator. This JSON file is completely autogenerated and all the configuration of the prompt generator is loaded from here in order to reduce the number of file access operations. The structure is also very optimized to minimize calculations that would be done live, ex does this entry exist in the pushed repos list, ok. In other words there's a lot of precomputed data here for the prompt. This file is also used to get the gitea origins as for me I have multiple organizations on my Gitea repo so I need to full path when switching between changes.

The file `set_repo.py` performs a switch on the git origin. https://git-scm.com/book/ms/v2/Git-Basics-Working-with-Remotes. A little known fact about git is you can have multiple origins and you can also switch between them, this is a great benefit of the git protocol being decentralized as it allows you to do this. This script works by taking the full repo path and checking the git remotes on the disk. If the remote is set to Github is searches the state file for the existing remotes. If the remote is set to Gitea then it first confirms that the remote exists on github by checking the state file and if so it computes\sets it to the respective remote.

The prompt generator which is located `src`, refered to as serpent (this is referenced in a lot of my projects and is a loose reference to the ecosystem of tools I have for myself) loads this state file and outputs the configured user (this is not the system user name rather it is what the user has configured\wants...for in the event these do not match) as well as the repo. The current directory is then checked to see if we are in a git repo. If we are in a git repo then we check to see if we are currently on gitea or github for the remote and we verify if the work has been pushed to Github (in which case we output prod...otherwise we output mvp). Of course we also output the branch information and whether all changes are committed.

## Setup, add these lines to your ~/.zshrc (change paths as appropriate):
```
function chpwd() {
    PROMPT=$(/opt/serpent)
}

function precmd() {
    PROMPT=$(/opt/serpent)
}

PROMPT=$(/opt/serpent)

alias pswitch='python /home/friedmicro/dev/dev-workflow/set_repo.py $(pwd)'
```

Make a copy of `serpentdevflowconfig.example.yaml` and change it to `serpentdevflowconfig.yaml`. Update the values as appropriate.

Build the serpent prompt binary with `cargo build --release` and move it to a location that makes sense to you.

## Use
To sync repos just run `python main.py`. It is expected that the requests library and pyyaml libraries are globally installed on your system, but most Linux distros ship with this. For mac you might need to load these in or create a virtualenv.

To switch the origin on a repo just run `pwswitch` in your terminal and it will switch between github\gitea.

Assuming you have added the lines above in setup to your zshrc and removed any existing prompt generators like ohmyzsh or starfish the prompt will just work.

## Notes and decision decisions\compromises
If you feel something is missing and would like that functionality please open a PR. You're also welcome to fork, this code is here to be usable for other engineers.

* The mvp\prod are hardcoded references, considering this is largely why I built this I feel this is fine, but it's worth noting that if it is not on an external repo then it's assumed the code is not prod. PRs are welcome for this.
* Only gitea and github are officialy supported for this project. PRs are welcome to add new providers on other side, but were not added because I do not use those.
* The prompt generator is in rust, but the git operations are in python. This is because cloning parallel can be quite computationally expensive on both the server and the client so I opted to skip this as the speed is suitable. If performance becomes an issue this will likely be rewritten into a more performance language like rust
* The access key for gitea is stored in plaintext and not in the keyring, this is for compatibility, but if you are concerned about access a seperate READONLY service user is a good recommentation
* Github assumes ssh for the origins so you need an SSH key. This is because I contribute to several open source systems that are ssh key only so I would much rather this be the default. A PR is welcome.
* Gitea assumes http for the origins. Candidly, very few self deployed Gitea instances I know of on internal network in this workflow use an SSH key and mine does not. A PR is welcome.
