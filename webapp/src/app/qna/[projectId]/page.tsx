import QNA from "@/components/QNA";
import { db } from "@/server/db";
import { auth } from "@clerk/nextjs";
import { notFound, redirect } from "next/navigation";
import React from "react";
type Props = {
  params: {
    projectId: string;
  };
};

const QNAPage = async ({ params: { projectId } }: Props) => {
  const { userId } = await auth();

  if (!userId) {
    return redirect("/sign-in");
  }

  try {
    const user = await db.user.findUnique({
      where: {
        id: userId,
      },
    });
    if (!user) {
      return redirect("/register-user");
    }

    const project = await db.project.findUnique({
      where: { id: projectId },
      include: {
        questions: {
          orderBy: {
            createdAt: "desc",
          },
          include: {
            user: true,
          },
        },
      },
    });
    if (!project) {
      return notFound();
    }
    return (
      <div>
        <QNA project={project} />
      </div>
    );
  } catch (error) {
    console.error("Database error in QNA page:", error);
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="max-w-md bg-red-50 border border-red-200 rounded-lg p-6">
          <h3 className="text-xl font-bold text-red-800 mb-2">Database Error</h3>
          <p className="text-red-700 mb-4">
            Unable to load Q&A data. Please try refreshing the page.
          </p>
          <a
            href={`/qna/${projectId}`}
            className="inline-block bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded"
          >
            Retry
          </a>
        </div>
      </div>
    );
  }
};

export default QNAPage;
