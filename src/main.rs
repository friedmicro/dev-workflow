use serde::Deserialize;
use std::env;
use std::fs;
use std::path::Path;
use std::path::PathBuf;
use std::process::Command;

#[derive(Deserialize)]
struct State {
    #[serde(default)]
    github_dirs: Vec<String>,
}

fn main() {
    let state = load_state();
    let user = "lucia";

    let (is_git_repo, dir_name, cwd) = handle_git_repo_switch(user);
    if !is_git_repo {
        return;
    }

    let host = handle_origin(&cwd);
    let tier = handle_tier(&dir_name, &state);

    let symbol = if is_clean(&cwd) {
        color("\u{2705} ", Color::Green)
    } else {
        color("\u{274C} ", Color::Red)
    };

    let branch = branch_name(&cwd);
    let git_part = format!(
        "git:({}\\{}\\{})",
        color(&branch, Color::Cyan),
        color(host, Color::Magenta),
        color(tier, Color::Yellow)
    );

    println!(
        "{}@{} {} {}",
        color(user, Color::Red),
        color(&dir_name, Color::Blue),
        color(&git_part, Color::Red),
        symbol
    );
}

// Recreating cmd and infering information twice is expensive considering the goal is for this shell to be fast
// Favor speed over reaability here
fn handle_git_repo_switch(user: &str) -> (bool, String, PathBuf) {
    let cwd = match env::current_dir() {
        Ok(dir) => dir,
        Err(e) => {
            eprintln!("error: unable to determine current directory: {}", e);
            std::process::exit(1);
        }
    };
    let dir_name = cwd
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_else(|| cwd.to_string_lossy().into_owned());

    if !is_git_repo(&cwd) {
        println!(
            "{}@{} ",
            color(user, Color::Red),
            color(&dir_name, Color::Blue)
        );
        return (false, dir_name, cwd);
    } else {
        return (true, dir_name, cwd);
    }
}

fn handle_origin(cwd: &PathBuf) -> &'static str {
    let origin = origin_url(&cwd);
    let host = if origin.to_lowercase().contains("github") {
        "github"
    } else {
        "gitea"
    };
    return host;
}

fn handle_tier(dir_name: &String, state: &State) -> &'static str {
    let tier = if state
        .github_dirs
        .iter()
        .any(|d| d.as_str() == dir_name.as_str())
    {
        "prod"
    } else {
        "mvp"
    };
    return tier;
}

fn load_state() -> State {
    let path = env::var("SERPENT_STATE_FILE").unwrap_or_else(|_| {
        let home = env::var("HOME").unwrap_or_else(|_| ".".to_string());
        format!("{}/.serpent-shell.json", home)
    });

    match fs::read_to_string(&path) {
        Ok(contents) => serde_json::from_str(&contents).unwrap_or_else(|e| {
            eprintln!(
                "warning: could not parse state file '{}': {}; defaulting to empty",
                path, e
            );
            State {
                github_dirs: Vec::new(),
            }
        }),
        Err(e) => {
            eprintln!(
                "warning: could not read state file '{}': {}; defaulting to empty",
                path, e
            );
            State {
                github_dirs: Vec::new(),
            }
        }
    }
}

fn git(cwd: &Path, args: &[&str]) -> Option<String> {
    let out = Command::new("git")
        .args(args)
        .current_dir(cwd)
        .output()
        .ok()?;
    if !out.status.success() {
        return None;
    }
    let text = String::from_utf8_lossy(&out.stdout).trim().to_string();
    Some(text)
}

fn is_git_repo(cwd: &Path) -> bool {
    git(cwd, &["rev-parse", "--is-inside-work-tree"])
        .map(|s| s == "true")
        .unwrap_or(false)
}

fn branch_name(cwd: &Path) -> String {
    if let Some(b) = git(cwd, &["symbolic-ref", "--short", "HEAD"]) {
        return b;
    }
    git(cwd, &["rev-parse", "--short", "HEAD"]).unwrap_or_else(|| "unknown".to_string())
}

fn origin_url(cwd: &Path) -> String {
    git(cwd, &["config", "--get", "remote.origin.url"]).unwrap_or_default()
}

fn is_clean(cwd: &Path) -> bool {
    let out = Command::new("git")
        .args(["status", "--porcelain"])
        .current_dir(cwd)
        .output();
    match out {
        Ok(o) => o.stdout.is_empty(),
        Err(_) => false,
    }
}

enum Color {
    Red,
    Green,
    Blue,
    Cyan,
    Magenta,
    Yellow,
}

fn color(text: &str, c: Color) -> String {
    let code = match c {
        Color::Red => "31",
        Color::Green => "32",
        Color::Blue => "34",
        Color::Cyan => "36",
        Color::Magenta => "35",
        Color::Yellow => "33",
    };
    format!("%{{\x1b[{}m%}}{}%{{\x1b[0m%}}", code, text)
}
