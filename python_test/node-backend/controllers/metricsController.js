const { makeRequest } = require('../utils/httpClient');

const getMetrics = async (req, res) => {
  try {
    const data = await makeRequest('/metrics');
    res.json(data);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
};

module.exports = { getMetrics };
