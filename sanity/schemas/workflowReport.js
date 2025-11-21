export default {
  name: 'workflowReport',
  title: 'Workflow Report',
  type: 'document',
  fields: [
    {
      name: 'repo',
      title: 'Repository',
      type: 'string',
      description: 'Repository identifier (e.g., owner/repository)',
      validation: Rule => Rule.required()
    },
    {
      name: 'team',
      title: 'Team',
      type: 'string',
      description: 'Team name or identifier',
      validation: Rule => Rule.required()
    },
    {
      name: 'score',
      title: 'Workflow Health Score',
      type: 'number',
      description: 'Overall workflow health score (0-100)',
      validation: Rule => Rule.required().min(0).max(100)
    },
    {
      name: 'bottlenecks',
      title: 'Bottlenecks',
      type: 'array',
      of: [{ type: 'string' }],
      description: 'List of identified workflow bottlenecks',
      validation: Rule => Rule.required().min(1).max(10)
    },
    {
      name: 'sop',
      title: 'Standard Operating Procedure',
      type: 'text',
      description: 'Generated SOP recommendations',
      rows: 10,
      validation: Rule => Rule.required().max(5000)
    },
    {
      name: 'metrics',
      title: 'Workflow Metrics',
      type: 'object',
      description: 'Detailed workflow metrics and measurements',
      fields: [
        {
          name: 'avgTimeToFirstReviewH',
          title: 'Average Time to First Review (hours)',
          type: 'number',
          validation: Rule => Rule.min(0)
        },
        {
          name: 'avgTimeToMergeH',
          title: 'Average Time to Merge (hours)',
          type: 'number',
          validation: Rule => Rule.min(0)
        },
        {
          name: 'unassigned24hRate',
          title: 'Unassigned 24h Rate',
          type: 'number',
          description: 'Percentage of issues unassigned after 24h',
          validation: Rule => Rule.min(0).max(1)
        },
        {
          name: 'reopenRate',
          title: 'Issue Reopen Rate',
          type: 'number',
          description: 'Percentage of issues that get reopened',
          validation: Rule => Rule.min(0).max(1)
        },
        {
          name: 'stale7dRatio',
          title: 'Stale 7-day Ratio',
          type: 'number',
          description: 'Ratio of issues stale for 7+ days',
          validation: Rule => Rule.min(0).max(1)
        },
        {
          name: 'windowDays',
          title: 'Analysis Window (days)',
          type: 'number',
          description: 'Number of days analyzed',
          validation: Rule => Rule.required().min(1).max(90)
        }
      ]
    },
    {
      name: 'version',
      title: 'Report Version',
      type: 'number',
      description: 'Version number of the report schema/format',
      initialValue: 1,
      validation: Rule => Rule.required().min(1)
    },
    {
      name: 'createdAt',
      title: 'Created At',
      type: 'datetime',
      description: 'When the report was generated',
      initialValue: () => new Date().toISOString(),
      validation: Rule => Rule.required()
    }
  ],
  preview: {
    select: {
      title: 'repo',
      subtitle: 'team',
      score: 'score',
      createdAt: 'createdAt'
    },
    prepare(selection) {
      const { title, subtitle, score, createdAt } = selection
      const date = createdAt ? new Date(createdAt).toLocaleDateString() : 'Unknown'
      return {
        title: `${title} (${subtitle})`,
        subtitle: `Score: ${score} | ${date}`,
        media: null
      }
    }
  },
  orderings: [
    {
      title: 'Created Date (newest first)',
      name: 'createdDesc',
      by: [{ field: 'createdAt', direction: 'desc' }]
    },
    {
      title: 'Score (highest first)',
      name: 'scoreDesc',
      by: [{ field: 'score', direction: 'desc' }]
    },
    {
      title: 'Repository',
      name: 'repoAsc',
      by: [{ field: 'repo', direction: 'asc' }]
    }
  ]
}