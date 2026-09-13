#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const LOGIN = process.env.GITHUB_LOGIN || "jvS0uzx";
const TOKEN = process.env.GITHUB_TOKEN;
const ISOMETRIC_DIR = process.env.ISOMETRIC_DIR;
const OUT_DIR = process.env.OUT_DIR || "assets";

const WIDTH = 1000;
const HEIGHT = 600;
const LABEL_COLOR = "#8b949e";

const RENDERER_TRANSLATIONS = [
  ['"en-US"', '"pt-BR"'],
  ['month: "short"', 'month: "2-digit"'],
  ['day: "numeric"', 'day: "2-digit"'],
  [".toLocaleString()", '.toLocaleString("pt-BR")'],
  ["stats.averageCount.toString()", 'stats.averageCount.toLocaleString("pt-BR")'],
  ['"Contributions"', '"Contribuições"'],
  ['"This week"', '"Esta semana"'],
  ['"Best day"', '"Recorde"'],
  ['"Average:"', '"Média:"'],
  ['"/ day"', '"/ dia"'],
  ['"Streaks"', '"Sequências"'],
  ['"day" : "days"', '"dia" : "dias"'],
  ['"0 days"', '"0 dias"'],
  ['"Longest"', '"Mais longa"'],
  ['"Current"', '"Atual"'],
  ['"No longest streak"', '"Sem sequência"'],
  ['"No current streak"', '"Sem sequência atual"'],
];

const PRIVATE_QUERY = `
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      restrictedContributionsCount
      commitContributionsByRepository(maxRepositories: 100) { repository { isPrivate } contributions { totalCount } }
      issueContributionsByRepository(maxRepositories: 100) { repository { isPrivate } contributions { totalCount } }
      pullRequestContributionsByRepository(maxRepositories: 100) { repository { isPrivate } contributions { totalCount } }
      pullRequestReviewContributionsByRepository(maxRepositories: 100) { repository { isPrivate } contributions { totalCount } }
      repositoryContributions(first: 100) { nodes { repository { isPrivate } } }
    }
  }
}`;

function importRenderer(file) {
  return import(pathToFileURL(resolve(ISOMETRIC_DIR, file)).href);
}

function translatedRendererPath() {
  const source = resolve(ISOMETRIC_DIR, "src/renderer.js");
  let code = readFileSync(source, "utf8");
  for (const [from, to] of RENDERER_TRANSLATIONS) {
    if (!code.includes(from)) {
      throw new Error(`renderer text not found for translation: ${from}`);
    }
    code = code.replaceAll(from, to);
  }
  const target = resolve(ISOMETRIC_DIR, "src/renderer.pt-BR.js");
  writeFileSync(target, code);
  return "src/renderer.pt-BR.js";
}

function rollingWindow() {
  const to = new Date();
  const from = new Date(to.getTime() - 364 * 24 * 60 * 60 * 1000);
  from.setHours(0, 0, 0, 0);
  return { from, to };
}

async function countPrivateContributions() {
  const { from, to } = rollingWindow();
  const response = await fetch("https://api.github.com/graphql", {
    method: "POST",
    headers: { Authorization: `bearer ${TOKEN}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      query: PRIVATE_QUERY,
      variables: { login: LOGIN, from: from.toISOString(), to: to.toISOString() },
    }),
  });
  if (!response.ok) {
    throw new Error(`GitHub API error: ${response.status} ${response.statusText}`);
  }
  const json = await response.json();
  if (json.errors) {
    throw new Error(`GitHub GraphQL error: ${json.errors[0].message}`);
  }

  const collection = json.data.user.contributionsCollection;
  let count = collection.restrictedContributionsCount;
  for (const key of [
    "commitContributionsByRepository",
    "issueContributionsByRepository",
    "pullRequestContributionsByRepository",
    "pullRequestReviewContributionsByRepository",
  ]) {
    for (const entry of collection[key]) {
      if (entry.repository.isPrivate) count += entry.contributions.totalCount;
    }
  }
  count += collection.repositoryContributions.nodes.filter((n) => n.repository.isPrivate).length;
  return count;
}

function captionSvg(privateCount, total) {
  const text =
    `${privateCount.toLocaleString("pt-BR")} de ${total.toLocaleString("pt-BR")} ` +
    "contribuições no último ano foram feitas em repositórios privados";
  const width = Math.ceil(text.length * 7.4) + 20;
  return `<svg width="${width}" height="28" viewBox="0 0 ${width} 28" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="${text}">
  <text x="${width / 2}" y="18" text-anchor="middle" font-family="'Segoe UI', Helvetica, Arial, sans-serif" font-size="13" fill="${LABEL_COLOR}">${text}</text>
</svg>
`;
}

async function main() {
  if (!TOKEN || !ISOMETRIC_DIR) {
    throw new Error("GITHUB_TOKEN and ISOMETRIC_DIR are required");
  }

  const { fetchContributions, parseContributionsData } = await importRenderer("src/api-client.js");
  const { renderWithStats, exportToPNG, setTheme } = await importRenderer(translatedRendererPath());
  const { OCEAN_THEME } = await importRenderer("src/theme-config.js");

  setTheme(OCEAN_THEME);
  const days = parseContributionsData(await fetchContributions(LOGIN, "none"), true);
  if (days.length < 180) {
    throw new Error(`only ${days.length}/365 days returned, not overwriting the graph`);
  }
  const total = days.reduce((sum, day) => sum + day.count, 0);
  const privateCount = await countPrivateContributions();

  mkdirSync(OUT_DIR, { recursive: true });
  const canvas = renderWithStats(days, { width: WIDTH, height: HEIGHT, username: null });
  writeFileSync(join(OUT_DIR, "contributions.png"), exportToPNG(canvas));
  writeFileSync(join(OUT_DIR, "private-contributions.svg"), captionSvg(privateCount, total));
  console.log(`wrote ${OUT_DIR}/contributions.png and ${OUT_DIR}/private-contributions.svg (${privateCount}/${total} private)`);
}

main().catch((error) => {
  console.error(`error: ${error.message}`);
  process.exit(1);
});
