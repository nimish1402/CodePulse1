import AddRepo from "@/components/AddRepo";
import ApplicationShell from "@/components/ApplicationShell";
import CreateProject from "@/components/CreateProject";
import { db } from "@/server/db";
import { auth } from "@clerk/nextjs";
import { redirect } from "next/navigation";

export default async function Index() {
  const { userId } = await auth();

  if (!userId) {
    return redirect("/sign-in");
  }

  try {
    // Wrap database queries in try-catch to handle connection errors
    const user = await db.user.findUnique({
      where: {
        id: userId,
      },
    });

    if (!user) {
      return redirect("/register-user");
    }

    const projects = await db.project.findMany({
      where: {
        users: {
          some: {
            id: user.id,
          },
        },
      },
    });

    if (projects.length === 0) {
      return (
        <>
          <h1 className="text-2xl font-semibold text-gray-700">
            Begin by creating a new project!
          </h1>
          <CreateProject />
        </>
      );
    } else {
      return redirect("/projects/" + projects[0]!.id);
    }
  } catch (error) {
    // Handle database connection errors gracefully
    console.error("Database error in Index page:", error);
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-8">
        <div className="max-w-md w-full bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-2xl font-bold text-red-800 mb-4">
            ⚠️ Database Connection Error
          </h2>
          <p className="text-red-700 mb-4">
            We're having trouble connecting to the database. This could be due to:
          </p>
          <ul className="list-disc list-inside text-red-600 mb-6 space-y-2">
            <li>Database server is temporarily unavailable</li>
            <li>Network connectivity issues</li>
            <li>Invalid database credentials</li>
          </ul>
          <div className="flex gap-3">
            <a
              href="/"
              className="flex-1 bg-red-600 hover:bg-red-700 text-white font-semibold py-2 px-4 rounded text-center transition-colors"
            >
              Retry
            </a>
            <a
              href="/sign-in"
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-semibold py-2 px-4 rounded text-center transition-colors"
            >
              Sign Out
            </a>
          </div>
        </div>
      </div>
    );
  }
}
