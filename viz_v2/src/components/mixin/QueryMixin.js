import { mapGetters } from 'vuex'
import * as config from '../../config.json'

export default {
  name: 'QueryMixin',
  data () {
    return {
      conf: config.default
    }
  },
  computed: {
    ...mapGetters({
      timeRange: 'getDataTimeRange'
      // monthlyStart: 'getMonthlyTrendStart'
    }),
    table () {
      return `${this.conf.projectId}.${this.conf.datasetID}.${this.conf.dataTable}`
    },
    dailyTimelineQuery () {
      return `SELECT day, sum(cd) 
                OVER (partition by day) as day_total
                FROM 
                (SELECT date(timestamp) as day, count(distinct id) as cd 
                  FROM \`${this.table}\` 
                  WHERE 
                  timestamp BETWEEN TIMESTAMP('${this.timeRange.startTime}') AND TIMESTAMP('${this.timeRange.endTime}')
                  AND RockV6_1_TOXICITY > .8
                  GROUP BY day )
                `
    },
    monthlyTimelineQuery () {
      return `WITH total AS 
                (SELECT month, sum(cd) 
                  OVER (partition by month) as month_total
                  FROM 
                    (SELECT 
                        DATE_TRUNC(DATE(timestamp), MONTH) as month, 
                        count(distinct id) as cd 
                      FROM  \`${this.table}\` 
                      WHERE
                        timestamp BETWEEN TIMESTAMP('2017-01-01') AND TIMESTAMP('2018-07-01')
                      AND RockV6_1_TOXICITY > .8
                      GROUP BY month )
                ),
                detox AS 
                  (SELECT demonth, sum(cd) 
                    OVER (partition by demonth) as detox_total
                    FROM 
                      (SELECT 
                        DATE_TRUNC(DATE(timestamp), MONTH) as demonth, 
                        count(distinct id) as cd 
                      FROM \`${this.table}\` 
                      WHERE 
                        timestamp BETWEEN TIMESTAMP('2016-12-31') AND TIMESTAMP('2018-07-01')
                      AND RockV6_1_TOXICITY > .8 AND type = 'DELETION'
                      GROUP BY demonth )
                )
                SELECT month, month_total, detox_total
                  FROM total
                  JOIN detox ON total.month = detox.demonth 
                  ORDER BY total.month DESC
                `
    },
    dataQuery () {
      return `SELECT 
                    RockV6_1_TOXICITY, RockV6_1_FLIRTATION, RockV6_1_TOXICITY_THREAT, RockV6_1_TOXICITY_IDENTITY_HATE, RockV6_1_TOXICITY_INSULT, RockV6_1_SEXUALLY_EXPLICIT, RockV6_1_TOXICITY_OBSCENE, RockV6_1_SEVERE_TOXICITY,
                    category1, sub_category1,
                    category2, sub_category2,
                    category3, sub_category3,
                    page_id, page_title, id, 
                    user_text, timestamp, 
                    cleaned_content, type 
                FROM \`${this.table}\` 
                  WHERE 
                  timestamp BETWEEN TIMESTAMP('${this.timeRange.startTime}') AND TIMESTAMP('${this.timeRange.endTime}')
                      AND RockV6_1_TOXICITY > .8
                      `
    }
  },
  methods: {
    getQuery (query) {
      return new Promise((resolve, reject) => {
        this.$getGapiClient()
          .then(gapi => {
            gapi.client.load('bigquery', 'v2', async () => {
              const options = {
                projectId: this.conf.projectId,
                query: query,
                useLegacySql: false,
                timeoutMs: 10000
              }
              try {
                const results = await gapi.client.bigquery.jobs.query(options)
                resolve(results.result.rows)
              } catch (error) {
                reject(error)
              }
            })
          })
      })
    }
  }
}
