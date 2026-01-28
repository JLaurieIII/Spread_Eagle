import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Meet Baldy: The Spread Eagle Who Picks College Basketball Games",
  description:
    "Meet Baldy—Spread Eagle's patriotic Philly bald eagle who drops one AI-generated college basketball preview per game per day. Funny. Sharp. Cached.",
};

export default function MeetBaldyLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
