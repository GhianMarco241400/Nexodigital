<!-- LOVABLE:BEGIN -->
> [!IMPORTANT]
> This project is connected to [Lovable](https://lovable.dev). Avoid rewriting
> published git history — force pushing, or rebasing/amending/squashing commits
> that are already pushed — as it rewrites history on Lovable's side and the
> user will likely lose their project history.
>
> Commits you push to the connected branch sync back to Lovable and show up in
> the editor, so keep the branch in a working state.
<!-- LOVABLE:END -->

## SalesIA architecture
- Keep fictional domain records and TypeScript interfaces in src/data; screens import examples rather than embedding business records.
- Use TanStack file routes for each module and a shared root shell with a demo-role context; role visibility is presentation only, not authentication.
- Use shared table, panel, filter and state controls for consistent frontend-only interactions; never persist mutations or connect a backend for the visual demo.
- Use Recharts for all statistical and sales charts, with colors sourced from semantic global CSS tokens.
