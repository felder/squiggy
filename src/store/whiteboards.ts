import _ from 'lodash'
import {getUsers} from '@/api/users'
import {getWhiteboards} from '@/api/whiteboards'

const orderByDefault = 'recent'

const fetch = (includeDeleted, limit, offset, orderBy) => getWhiteboards(includeDeleted, limit, offset, orderBy)

const $_search = (commit, state, addToExisting?: boolean) => {
  return new Promise(resolve => {
    fetch(state.includeDeleted, state.limit, state.offset, state.orderBy).then(data => {
      const whiteboards = _.get(data, 'results')
      commit(addToExisting ? 'addWhiteboards' : 'setWhiteboards', whiteboards)
      commit('setTotalWhiteboardCount', _.get(data, 'total'))
      commit('setDirty', false)
      resolve(data)
    })
  })
}

const state = {
  whiteboards: undefined,
  collaborators: undefined,
  collaborator: undefined,
  expanded: undefined,
  includeDeleted: false,
  isDirty: false,
  keywords: undefined,
  limit: 20,
  offset: 0,
  orderBy: orderByDefault,
  sectionId: undefined,
  totalWhiteboardCount: undefined,
  userId: undefined,
  users: undefined
}

const getters = {
  whiteboards: (state: any): any[] => state.whiteboards,
  collaborators: (state: any): any[] => state.collaborators,
  collaborator: (state: any): number => state.collaborator,
  expanded: (state: any): boolean => state.expanded,
  includeDeleted: (state: any): boolean => state.includeDeleted,
  isDirty: (state: any): boolean => state.isDirty,
  keywords: (state: any): string => state.keywords,
  limit: (state: any): number => state.limit,
  orderBy: (state: any): string => state.orderBy,
  orderByDefault: (): string => orderByDefault,
  totalWhiteboardCount: (state: any): number => state.totalWhiteboardCount,
  userId: (state: any): number => state.userId,
  users: (state: any): any[] => state.users
}

const mutations = {
  addWhiteboards: (state: any, whiteboards: any[]) => state.whiteboards.push(...whiteboards),
  setWhiteboards: (state: any, whiteboards: any[]) => state.whiteboards = whiteboards,
  setCollaborators: (state: any, collaborators: any[]) => state.collaborators = collaborators,
  setCollaborator: (state: any, collaborator: number) => {
    state.collaborator = collaborator
    state.isDirty = true
  },
  setDirty: (state: any, dirty: boolean) => state.isDirty = dirty,
  setExpanded: (state: any, expanded: boolean) => state.expanded = expanded,
  setIncludeDeleted: (state: any, includeDeleted: boolean) => state.includeDeleted = includeDeleted,
  setKeywords: (state: any, keywords: string) => {
    state.keywords = keywords
    state.isDirty = true
  },
  setOffset: (state: any, offset: number) => state.offset = offset,
  setOrderBy: (state: any, orderBy: string) => {
    state.orderBy = orderBy
    state.isDirty = true
  },
  setUserId: (state: any, userId: number) => {
    state.userId = userId
    state.isDirty = true
  },
  setTotalWhiteboardCount: (state: any, count: number) => state.totalWhiteboardCount = count,
  setUsers: (state: any, users: any[]) => state.users = users,
  updateWhiteboardStore: (state: any, updatedWhiteboard: any) => {
    if (state.whiteboards) {
      _.each(state.whiteboards, whiteboard => {
        if (whiteboard.id === updatedWhiteboard.id) {
          Object.assign(whiteboard, updatedWhiteboard)
        }
      })
    }
  },
}

const actions = {
  init({commit}) {
    return new Promise<void>(resolve => {
      getUsers().then(data => {
        commit('setUsers', data)
        resolve()
      })
    })
  },
  nextPage: ({commit, state}) => {
    commit('setOffset', state.offset + state.limit)
    return $_search(commit, state, true)
  },
  refresh: ({commit, state}) => {
    return new Promise(resolve => {
      console.log(`Refreshing on ${new Date().getTime()}...`)
      fetch(
        state.includeDeleted,
        state.limit,
        0,
        state.orderBy,
      ).then(data => {
        const whiteboards = _.get(data, 'results')
        commit('setWhiteboards', whiteboards)
        commit('setTotalWhiteboardCount', _.get(data, 'total'))
        commit('setDirty', false)
        resolve(data)
      })
    })
  },
  resetSearch: ({commit}) => commit('setOffset', 0),
  search: ({commit, state}) => $_search(commit, state),
  setCollaborator: ({commit}, collaborator) => commit('setCollaborator', collaborator),
  setExpanded: ({commit}, expanded) => commit('setExpanded', expanded),
  setIncludeDeleted: ({commit}, includeDeleted) => commit('setIncludeDeleted', includeDeleted),
  setKeywords: ({commit}, keywords) => commit('setKeywords', keywords),
  setOrderBy: ({commit}, orderBy) => commit('setOrderBy', orderBy),
  setUserId: ({commit}, userId) => commit('setUserId', userId),
  updateWhiteboardStore: ({commit}, updatedWhiteboard) => commit('updateWhiteboardStore', updatedWhiteboard)
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}
