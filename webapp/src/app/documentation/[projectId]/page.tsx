import TipTapEditor from "@/components/TipTapEditor";
import { db } from "@/server/db";
import { auth } from "@clerk/nextjs";
import { notFound, redirect } from "next/navigation";
import React from "react";

type Props = {
  params: {
    projectId: string;
  };
};

const DocumentationPage = async ({ params: { projectId } }: Props) => {
  const { userId } = await auth();

  try {
    const user = await db.user.findUnique({
      where: {
        id: userId ?? "",
      },
    });
    if (!user) {
      return redirect("/register-user");
    }

    const project = await db.project.findUnique({
      where: { id: projectId },
    });
    if (!project) {
      return notFound();
    }
    return (
      <>
        <div className="rounded-lg p-4 shadow-xl">
          <TipTapEditor project={project} />
        </div>
      </>
    );
  } catch (error) {
    console.error("Database error in Documentation page:", error);
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="max-w-md bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-xl font-bold text-red-800 mb-2">Database Error</h3>
          <p className="text-red-700 mb-4">
            Unable to load documentation data. Please try refreshing the page.
          </p>
          <a
            href={`/documentation/${projectId}`}
            className="inline-block bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded"
          >
            Retry
          </a>
        </div>
      </div>
    );
  }
};

export default DocumentationPage;
