import type { User } from "@prisma/client";
import React from "react";
import { api } from "@/trpc/server";

type Props = {
  projectId: string;
  users: User[];
};

const TeamMembers = async ({ projectId, users }: Props) => {
  try {
    const avatars = await api.project.getUserAvatars.query({
      projectId,
    });
    return (
      <>
        <div className="flex -space-x-2 overflow-hidden">
          {users.map((user, index) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              key={user.id}
              className="inline-block h-8 w-8 rounded-full ring-2 ring-white"
              src={avatars[index]}
              alt="user profile"
            />
          ))}
        </div>
      </>
    );
  } catch (error) {
    // Fallback to initials if avatar fetch fails
    console.error("Error fetching user avatars:", error);
    return (
      <>
        <div className="flex -space-x-2 overflow-hidden">
          {users.map((user) => (
            <div
              key={user.id}
              className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-gray-500 ring-2 ring-white text-xs font-medium text-white"
            >
              {user.name?.charAt(0).toUpperCase() || "?"}
            </div>
          ))}
        </div>
      </>
    );
  }
};

export default TeamMembers;
