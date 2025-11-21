import {defineType, defineField} from "sanity";

export default defineType({
  name: "workflowReport",
  title: "Workflow Report",
  type: "document",
  fields: [
    defineField({
      name: "repo",
      title: "Repository",
      type: "string",
    }),
    defineField({
      name: "team",
      title: "Team",
      type: "string",
    }),
    defineField({
      name: "score",
      title: "Score",
      type: "number",
    }),
    defineField({
      name: "bottlenecks",
      title: "Bottlenecks",
      type: "array",
      of: [{type: "string"}],
    }),
    defineField({
      name: "sop",
      title: "SOP",
      type: "text",
    }),
    defineField({
      name: "metrics",
      title: "Metrics",
      type: "object",
      fields: [],
    }),
    defineField({
      name: "version",
      title: "Version",
      type: "number",
    }),
    defineField({
      name: "createdAt",
      title: "Created At",
      type: "datetime",
      initialValue: () => new Date().toISOString(),
    }),
  ],
});
